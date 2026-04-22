"""
CSV 上傳驗證模組：驗證檔名與欄位是否符合各廣告平台的 template 規格。
"""

import csv
import io
from typing import Type

from pydantic import BaseModel, ValidationError

from app.domain.exception.domain_exception import DomainException

# ── 允許的檔名 ──────────────────────────────────────────────────────────────

ALLOWED_FILENAMES = {"google_ads_template.csv", "meta_ads_template.csv"}


# ── Pydantic 行模型（同時作為欄位規格文件） ──────────────────────────────────


class GoogleAdsRow(BaseModel):
    """Google Ads template 每列的欄位規格。"""

    date: str  # 廣告日期 YYYY-mm-dd
    account_id: str  # 廣告帳號ID
    campaign_name: str  # 廣告活動
    ad_group_name: str  # 廣告群組
    ad_id: str
    image_ad_url: str  # 廣告圖片url
    headline_multi_asset: str  # 廣告標題欄位
    description_multi_asset: str  # 廣告說明欄位
    video_title: str  # 影片標題（影音廣告）
    video_url: str  # 影片youtube連結（影音廣告）
    ad_status_effective_status: str  # 廣告狀態
    impressions: int  # 曝光
    video_views: int  # 廣告觀看數
    clicks: int  # 廣告點擊
    cost: float  # 廣告費用
    conversions: float  # 轉換數
    conversions_value: float  # 轉換價值


class MetaAdsRow(BaseModel):
    """Meta Ads template 每列的欄位規格。"""

    date: str  # 廣告日期 YYYY-mm-dd
    account_id: str  # 廣告帳號ID
    campaign_name: str  # 廣告活動
    ad_set_name: str  # 廣告組合
    ad_name: str  # 廣告名稱
    ad_id: str  # 廣告id
    ad_image_url: str  # 廣告圖片url
    ad_status: str  # 廣告狀態
    impressions: int  # 曝光
    three_second_video_views: int  # 影音廣告觀看數
    clicks: int  # 廣告點擊
    cost: float  # 廣告費用
    conversions: float  # 轉換數
    conversions_value: float  # 轉換價值


# ── 檔名 → schema 對應表 ─────────────────────────────────────────────────────

_FILENAME_SCHEMA_MAP: dict[str, Type[BaseModel]] = {
    "google_ads_template.csv": GoogleAdsRow,
    "meta_ads_template.csv": MetaAdsRow,
}


# ── 共用驗證函式 ─────────────────────────────────────────────────────────────


def validate_csv_file(filename: str, content_bytes: bytes) -> None:
    """
    驗證 CSV 檔名與欄位是否符合規格。

    Args:
        filename:      上傳的原始檔名（例如 "google_ads_template.csv"）
        content_bytes: CSV 檔案的原始位元組內容

    Raises:
        DomainException: 檔名不符或欄位缺少／多餘時拋出 400。
    """
    _validate_filename(filename)
    _validate_columns(filename, content_bytes)


def _validate_filename(filename: str) -> None:
    if filename not in ALLOWED_FILENAMES:
        allowed = ", ".join(sorted(ALLOWED_FILENAMES))
        raise DomainException(
            msg=f"Invalid filename '{filename}'. Allowed filenames: {allowed}",
            type="invalid_filename",
            code=400,
        )


def _validate_columns(filename: str, content_bytes: bytes) -> None:
    schema_cls = _FILENAME_SCHEMA_MAP[filename]
    expected_cols: set[str] = set(schema_cls.model_fields.keys())

    try:
        text = content_bytes.decode("utf-8-sig")  # utf-8-sig 自動去除 BOM
        reader = csv.reader(io.StringIO(text))
        raw_headers = next(reader, None)
    except UnicodeDecodeError:
        raise DomainException(
            msg="CSV file must be UTF-8 encoded",
            type="invalid_encoding",
            code=400,
        )

    if raw_headers is None:
        raise DomainException(
            msg="CSV file is empty or has no header row",
            type="invalid_csv",
            code=400,
        )

    actual_cols = {h.strip() for h in raw_headers}
    missing = expected_cols - actual_cols
    extra = actual_cols - expected_cols

    if missing or extra:
        parts: list[str] = []
        if missing:
            parts.append(f"missing columns: {', '.join(sorted(missing))}")
        if extra:
            parts.append(f"unexpected columns: {', '.join(sorted(extra))}")
        raise DomainException(
            msg=f"CSV column mismatch for '{filename}' — {'; '.join(parts)}",
            type="invalid_csv_columns",
            code=400,
        )

    # 跳過第 2～4 列（說明列），從第 5 列開始驗證型別
    stripped_headers = [h.strip() for h in raw_headers]
    for row_num, row in enumerate(reader, start=2):
        row_dict = dict(zip(stripped_headers, row))
        try:
            schema_cls.model_validate(row_dict)
        except ValidationError as exc:
            field_errors = "; ".join(
                f"欄位 '{e['loc'][0]}' 值 '{row_dict.get(str(e['loc'][0]), '')}' 型別錯誤（預期 {e['type']}）"
                for e in exc.errors()
            )
            raise DomainException(
                msg=f"CSV 第 {row_num} 列型別錯誤 — {field_errors}",
                type="invalid_csv_type",
                code=400,
            )

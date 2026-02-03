# -*- coding: utf-8 -*-
"""
UI Drift 分析工具

讀取 AI 觀測知識庫，對比 TestPlan.xlsx 中的 Translate 表，
找出哪些 ActionKey 的描述與實際 UI 標籤已經產生偏離 (Drift)。

產出 Markdown 格式的欄位修改建議報告。

Author: SDET Team
Date: 2026-02-03
"""

import json
import sys
import os
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import pandas as pd

# 添加專案根目錄到 sys.path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import DevConfig


class UIDriftAnalyzer:
    """UI 變動偏離分析器"""
    
    def __init__(
        self,
        knowledge_base_path: str = None,
        testplan_path: str = None
    ):
        """
        初始化分析器
        
        Args:
            knowledge_base_path: AI 知識庫 JSON 路徑
            testplan_path: TestPlan.xlsx 路徑
        """
        self.knowledge_base_path = knowledge_base_path or os.path.join(
            DevConfig.AI_INTELLIGENCE_LOG_DIR, "knowledge_base.json"
        )
        self.testplan_path = testplan_path or DevConfig.TEST_PLAN_PATH
        
        self.knowledge_base = None
        self.translate_df = None
        self.drift_reports = []
    
    def load_knowledge_base(self) -> bool:
        """
        載入 AI 觀測知識庫
        
        Returns:
            是否成功載入
        """
        if not os.path.exists(self.knowledge_base_path):
            print(f"❌ 知識庫文件不存在: {self.knowledge_base_path}")
            return False
        
        try:
            with open(self.knowledge_base_path, "r", encoding="utf-8") as f:
                self.knowledge_base = json.load(f)
            
            obs_count = len(self.knowledge_base.get("observations", []))
            print(f"✅ 已載入知識庫: {obs_count} 筆觀測記錄")
            return True
            
        except Exception as e:
            print(f"❌ 載入知識庫失敗: {e}")
            return False
    
    def load_testplan(self) -> bool:
        """
        載入 TestPlan.xlsx 的 Translate 表
        
        Returns:
            是否成功載入
        """
        if not os.path.exists(self.testplan_path):
            print(f"❌ TestPlan 文件不存在: {self.testplan_path}")
            return False
        
        try:
            self.translate_df = pd.read_excel(
                self.testplan_path, 
                sheet_name="Translate"
            )
            print(f"✅ 已載入 Translate 表: {len(self.translate_df)} 筆 ActionKey")
            return True
            
        except Exception as e:
            print(f"❌ 載入 TestPlan 失敗: {e}")
            return False
    
    def analyze_drift(self) -> List[Dict[str, Any]]:
        """
        分析 UI 偏離情況
        
        Returns:
            偏離報告列表
        """
        if not self.knowledge_base or self.translate_df is None:
            print("❌ 請先載入知識庫和 TestPlan")
            return []
        
        observations = self.knowledge_base.get("observations", [])
        
        for obs in observations:
            target = obs.get("target", "")
            vlm_analysis = obs.get("vlm_analysis", {})
            
            # 查找對應的 ActionKey
            matching_rows = self.translate_df[
                self.translate_df["ActionKey"] == target
            ]
            
            if matching_rows.empty:
                # ActionKey 不存在於 Translate 表
                self.drift_reports.append({
                    "type": "missing_action_key",
                    "action_key": target,
                    "timestamp": obs.get("timestamp"),
                    "recommended_key": vlm_analysis.get("recommended_action_key"),
                    "description": vlm_analysis.get("potential_changes"),
                    "severity": vlm_analysis.get("severity", "low")
                })
            else:
                # ActionKey 存在，檢查是否需要更新
                current_desc = matching_rows.iloc[0].get("Description", "")
                observed_labels = vlm_analysis.get("observed_elements", [])
                
                # 簡單的相似度檢查（實際可用更複雜的演算法）
                if observed_labels and not any(
                    elem.get("label", "").lower() in current_desc.lower()
                    for elem in observed_labels
                ):
                    self.drift_reports.append({
                        "type": "description_drift",
                        "action_key": target,
                        "current_description": current_desc,
                        "observed_labels": [e.get("label") for e in observed_labels],
                        "recommended_update": vlm_analysis.get("recommended_locator"),
                        "timestamp": obs.get("timestamp"),
                        "severity": vlm_analysis.get("severity", "medium")
                    })
        
        print(f"📊 分析完成: 發現 {len(self.drift_reports)} 個潛在偏離")
        return self.drift_reports
    
    def generate_report(self, output_path: str = None) -> str:
        """
        生成 Markdown 格式的偏離報告
        
        Args:
            output_path: 輸出文件路徑（可選）
            
        Returns:
            Markdown 報告內容
        """
        if not self.drift_reports:
            return "# UI Drift 分析報告\n\n✅ 未發現 UI 偏離情況"
        
        # 構建 Markdown 報告
        report_lines = [
            "# UI Drift 分析報告",
            "",
            f"**生成時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**總偏離數**: {len(self.drift_reports)}",
            "",
            "---",
            ""
        ]
        
        # 按嚴重程度分組
        high_severity = [r for r in self.drift_reports if r.get("severity") == "high"]
        medium_severity = [r for r in self.drift_reports if r.get("severity") == "medium"]
        low_severity = [r for r in self.drift_reports if r.get("severity") == "low"]
        
        for severity, reports in [
            ("🔴 高優先級", high_severity),
            ("🟡 中優先級", medium_severity),
            ("🟢 低優先級", low_severity)
        ]:
            if not reports:
                continue
            
            report_lines.append(f"## {severity}")
            report_lines.append("")
            
            for i, drift in enumerate(reports, 1):
                if drift["type"] == "missing_action_key":
                    report_lines.extend([
                        f"### {i}. 缺失的 ActionKey: `{drift['action_key']}`",
                        "",
                        f"- **時間戳**: {drift['timestamp']}",
                        f"- **建議新增**: `{drift['recommended_key']}`",
                        f"- **描述**: {drift['description']}",
                        "",
                        "**建議操作**:",
                        f"1. 在 Translate 表中新增 ActionKey: `{drift['recommended_key']}`",
                        "2. 更新對應的 Flow 定義",
                        ""
                    ])
                elif drift["type"] == "description_drift":
                    report_lines.extend([
                        f"### {i}. 描述偏離: `{drift['action_key']}`",
                        "",
                        f"- **時間戳**: {drift['timestamp']}",
                        f"- **當前描述**: {drift['current_description']}",
                        f"- **觀測到的標籤**: {', '.join(drift['observed_labels'])}",
                        f"- **建議定位器**: `{drift['recommended_update']}`",
                        "",
                        "**建議操作**:",
                        "1. 更新 Translate 表中的 Description",
                        "2. 驗證新的定位策略是否有效",
                        ""
                    ])
            
            report_lines.append("---")
            report_lines.append("")
        
        report_content = "\n".join(report_lines)
        
        # 保存到文件
        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(report_content)
            print(f"📝 報告已保存: {output_path}")
        
        return report_content


def main():
    """主函數"""
    print("=" * 60)
    print("UI Drift 分析工具")
    print("=" * 60)
    print()
    
    analyzer = UIDriftAnalyzer()
    
    # 載入數據
    if not analyzer.load_knowledge_base():
        return 1
    
    if not analyzer.load_testplan():
        return 1
    
    # 分析偏離
    analyzer.analyze_drift()
    
    # 生成報告
    output_path = os.path.join(
        DevConfig.AI_INTELLIGENCE_LOG_DIR,
        f"ui_drift_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    )
    
    report = analyzer.generate_report(output_path)
    
    print()
    print("=" * 60)
    print("報告預覽:")
    print("=" * 60)
    print(report[:500])  # 顯示前 500 字符
    print("...")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

# MigraAgent

MigraAgent 是一个可本地运行的 Python 3.10+ 示例项目，用于演示**基于多 Agent 协作的遗留系统智能迁移与兼容性适配平台**的核心流程。

项目重点能力：

- 多 Agent 协作：`ScannerAgent -> RiskAgent -> RefactorAgent -> ValidatorAgent`
- 风险 Agent 的长链推理：追溯调用关系、评估波及范围、估算测试覆盖缺口并计算风险分
- 自带遗留代码示例与测试
- 输出风险评估报告（JSON）并生成适配器包装类代码

---

## 1. 安装与运行

```bash
pip install -r requirements.txt
python run_migra_agent.py
```

运行后可看到：

- 扫描到的 API 清单
- 风险 Agent 的 Step-by-Step 推理过程
- 风险报告 JSON（同时写入 `examples/risk_report.json`）
- 生成的适配器文件（`examples/migrated_adapter.py`）
- 验证 Agent 的测试执行结果

---

## 2. 项目结构

```text
MigraAgent/
├─ README.md
├─ requirements.txt
├─ run_migra_agent.py
├─ migra_agent/
│  ├─ __init__.py
│  ├─ context.py
│  ├─ agents/
│  │  ├─ __init__.py
│  │  ├─ base_agent.py
│  │  ├─ scanner_agent.py
│  │  ├─ risk_agent.py
│  │  ├─ refactor_agent.py
│  │  └─ validator_agent.py
│  └─ graph/
│     ├─ __init__.py
│     └─ call_graph_builder.py
├─ examples/
│  ├─ __init__.py
│  ├─ legacy_code.py
│  ├─ test_legacy.py
│  ├─ migrated_adapter.py          # 运行后生成
│  └─ risk_report.json             # 运行后生成
└─ tests/
   └─ test_agents.py
```

---

## 3. 核心设计说明

### 多 Agent 协作

- `ScannerAgent`：解析 AST，识别函数、类、调用列表与已知过时 API。
- `RiskAgent`：基于调用图进行长链推理，输出分项评分与总风险。
- `RefactorAgent`：针对旧函数生成适配器包装类，保留接口并增加输入检查/日志。
- `ValidatorAgent`：调用 `pytest` 执行回归验证，形成闭环。

### 长链推理（RiskAgent）

`long_chain_reasoning(call_graph, target_api)` 主要步骤：

1. 分析目标 API 的直接调用者和直接被调函数（直接变更复杂度）
2. 深度优先追溯所有下游依赖（波及范围）
3. 深度优先追溯上游调用者（传播入口）
4. 根据测试调用推断覆盖缺口（测试风险）
5. 按权重聚合为总分并给出风险等级

---

## 4. 说明

- 依赖仅使用标准库 + `networkx`（可选调用图增强）+ `pytest`。
- 若 `networkx` 不可用，项目会自动退化到纯 `dict` 图结构，不影响主流程运行。

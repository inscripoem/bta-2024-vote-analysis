# 2024大二杯投票分析工具

这是一个用于分析2024大二杯投票数据的工具，可以帮助统计和分析投票结果，生成详细的报告与供[可视化网站](https://github.com/inscripoem/bta-2024-visualization-next)使用的序列化数据

## 技术栈

- Python 3.12.8
- 包管理工具：Rye
- 主要依赖：
  - pandas：数据处理和分析
  - numpy：数值计算
  - rich：终端输出美化
  - openpyxl：Excel文件处理
  - pypinyin：中文拼音转换
  - msgpack：数据序列化

## 项目结构

```
bta-2024-vote-analysis/
├── src/
│   └── bta_2024_vote_analysis/
│       ├── adapters/      # 数据适配器
│       ├── core/          # 核心业务逻辑
│       ├── infrastructure/# 基础设施代码
│       ├── __init__.py    # 主程序入口
│       └── __main__.py    # 命令行入口
├── .data/                 # 数据文件目录
└── pyproject.toml         # 项目配置
```

## 使用指南

### 环境设置

1. 安装 [Rye](https://rye.astral.sh)

2. 克隆项目并安装依赖：
   ```bash
   git clone <项目地址>
   cd bta-2024-vote-analysis
   rye sync
   ```

### 准备数据

将2024大二杯后端生成的 `answer_all.xlsx` 文件放置于 `.data` 目录下，或者修改 `src/bta_2024_vote_analysis/__init__.py` 中 `vote_loader` 变量的 `file_path` 参数到对应的文件路径

### 运行项目

1. 激活虚拟环境后可以通过以下方式运行：

```bash
bta-2024-vote-analysis
```

2. 也可以在不激活虚拟环境的情况下通过 Rye 运行：

```bash
rye run bta-2024-vote-analysis
```

应用将自动进行计算，日志保存在程序运行目录的 `logs` 目录下，结果将保存到程序运行目录的 `reports_refactor` 目录下。

### 使用结果

结果分为两部分：

- 直接可读的报告 `vote_analysis_report.md`
- 供[可视化网站](https://github.com/inscripoem/bta-2024-visualization-next)使用的序列化数据 `vote_analysis_report.json` 和 `vote_analysis_report.msgpack`，后者的数据结构可以参考 `vote_analysis_report_rev.json` 


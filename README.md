# SPARK AI Hackathon

<!-- [English](/docs/README_EN-US.md) | [简体中文](/docs/README_ZH-CN.md) -->

<!-- 
📌 占位符说明：
- [BANNER_IMAGE_PATH] - 活动主视觉图片路径
- [ACTIVITY_THEME] - 活动主题
- [REGISTRATION_FORM_LINK] - 报名表单链接
- [VIDEO_TUTORIAL_BILIBILI] - Bilibili 教程视频
- [VIDEO_TUTORIAL_YOUTUBE] - YouTube 教程视频
- [ZOOM_LINK] - Demo Day Zoom 链接
-->

🧬

## 📊 活动主视觉

![Agent Hack Banner][BANNER_IMAGE_PATH]

## 01 | 报名方式与议程安排

📍 线上举行｜自由报名（面向所有人）

| 活动                 | 时间                      | 形式    | 相关链接                                                        |
| -------------------- | ------------------------- | ------- | --------------------------------------------------------------- |
| **开始报名**   | [REGISTRATION_START_DATE] | 📍 线上 | **👉 [点击此处填写报名表](https://github.com/CasualHackathon/agenthack/issues/new?template=register.md)** |
| 🗓**Open Day** | [OPEN_DAY_DATE_TIME]      | 📍 线上 | **👉 [点击此处提交 Demo](https://github.com/CasualHackathon/agenthack/issues/new?template=submission.md)** |
| 🏁**Demo Day** | [DEMO_DAY_DATE_TIME]      | 📍 线上 | [Zoom 链接][ZOOM_LINK]                                          |

**报名教程：**

- [Bilibili][VIDEO_TUTORIAL_BILIBILI]
- [YouTube][VIDEO_TUTORIAL_YOUTUBE]

### **注意事项：**

1. 禁止修改他人信息。
2. 提交 Demo 时必须先完成注册，否则提交无效。
3. 提交资料时，只在对应位置填写信息，不要修改其它基础内容，特别是 issues title。
4. 提交报名后，预计1分钟内会显示在下方报名列表中，如未显示请联系相关技术人员。
5. 提交 Demo 时，请先 Fork 当前代码库，然后将 Demo 相关代码，放到以你 Github ID 命名的目录下，如：`/submission/[your-github-account]`，然后再提交 PR，我们会在审阅后合并，禁止修改其它信息。

## 📅 赛道介绍 (Tracks)

本次黑客松共设立三个核心赛道，你可以根据兴趣选择其一进行挑战。

### 1. 💸 支付赛道 (Payment Track)
> **支持方**: Kite AI 

**🎯 核心目标**
探索 AI/Agent 场景下的自动化支付、链上结算与资金流转方案。我们需要看到 AI 不仅仅是“聊天”，还能真正地“产生交易”。

**💡 开发灵感 (Ideas)**
* **AI 购物助手**：一个能根据用户指令，自动寻找并购买数字商品（如 NFT 或 API Key）的 Agent。
* **自动订阅管理**：监测服务状态，并在服务即将到期时自动调用钱包续费的后台 Agent。
* **多 Agent 结算网络**：Agent A 为 Agent B 提供数据，Agent B 自动向 Agent A 支付微支付（Micro-payment）。

**🛠 技术要求**
* 基于 Kite AI 提供的 API 或 SDK。
* 实现一个具备支付/结算功能的 Demo（Hello World 级别即可，重点是跑通流程）。

---

### 2. 🧠 LLM 应用赛道 (LLM Application Track)
> **支持方**: SpoonOS 

**🎯 核心目标**
基于 SpoonOS Framework 调用 LLM，构建可执行的 AI 应用 / Agent 工作流。这是本次奖金最丰厚的赛道，我们期待看到完整的逻辑闭环。

**💡 开发灵感 (Ideas)**
* **Crypto 投研分析师**：自动抓取推特/新闻 -> 总结情绪 -> 生成日报并发布。
* **社区治理 Mod**：自动回答 Discord/Telegram 群组中的技术问题，并整理常见 FAQ。
* **垂直领域助手**：法律文书生成器、代码审计初筛 Agent 等。

**🛠 技术要求**
* 必须使用 [SpoonOS Framework](https://www.notion.so/SpoonOS-Hackathon-2f1bbd63be8780db8c59c20349715dd5?pvs=21)。
* 提交的项目需展示完整的工作流（Input -> Processing -> Output）。

---

### 3. 🔮 预测市场赛道 (Prediction Market Track)
> **支持方**: OGBC × ScalingX 

**🎯 核心目标**
设计具备扩展性的预测市场结构、激励机制与数据输入方案。本赛道偏向于机制设计与合约逻辑的结合。

**💡 开发灵感 (Ideas)**
* **新闻事件预测市场**：结合 AI 预言机，当新闻发生时自动创建预测盘口。
* **KOL 影响力对赌**：基于社交媒体数据增长的预测合约。
* **去中心化赛事竞猜**：利用提供的底层逻辑文档，设计一个最小化的竞猜 DApp。

**🛠 技术要求**
* 参考官方提供的合约交互文档或逻辑架构图。
* 设计合理的激励机制（如何防止作恶，如何激励正确预测）。

### 🧰 特别工具支持 (Optional Tooling)
**DataDance SDK**

> *这是一个非强制的加分工具，适用于所有赛道的数据处理场景。*

* **推荐场景**: 需要进行复杂数据清洗、格式化或多源数据接入的项目（例如预测市场的数据源处理，或 LLM 的上下文预处理）。
* **文档**: [📄 DataDance SDK 使用指南](https://docs.google.com/document/d/1xbGWsV8spQXA2ZBCmN-xJjcNvdJEWwo77edUyXh0aKs/edit)
* **说明**: 鼓励选手尝试使用，可能会让你的 Demo 数据流转更加顺滑。

## 🛠 开发者资源 (Developer Resources)

为了让你专注于开发，我们整理了各赛道的“武器库”。

| 赛道 | 资源类型 | 说明与链接 |
| :--- | :--- | :--- |
| **Kite AI** | API/SDK | 包含“一键调用支付”接口文档（见仓库 `/docs/kite` 或官方链接） |
| | Demo 代码 | AI Agent 自动转账最小示例 (Hello World) |
| | 教程 | "AI 与支付链路打通" Workshop 视频/PPT |
| **SpoonOS** | **核心文档** | [**SpoonOS · 最低技术使用要求（Hackathon）**](https://www.notion.so/SpoonOS-Hackathon-2f1bbd63be8780db8c59c20349715dd5?pvs=21) 👈 **必读** |
| | 模板库 | 常见 Agent 工作流模板 (抓取 -> 总结 -> 发布) |
| | FAQ | 环境安装与模型调用报错排查手册 |
| | Workshop | Rick 老师的实战教学视频 |
| **OGBC x ScalingX** | 架构图 | 预测市场底层逻辑与合约交互图解（小白友好） |
| | 案例库 | 优秀预测市场项目参考案例 |
| | 实战题目 | 项目方发布的实战预测任务素材 |
| **DataDance** | SDK 文档 | [DataDance SDK 开发文档](https://docs.google.com/document/d/1xbGWsV8spQXA2ZBCmN-xJjcNvdJEWwo77edUyXh0aKs/edit) (处理数据神器) |

## 03 | 项目提交要求(Submission Guide)

**截止时间：** **2026.1.30 23:59 前（UTC+8）**

请通过 GitHub Issues 提交以下材料：

- ✅ 项目 GitHub 仓库（必须开源）
- ✅ 可选: 演示幻灯片（PDF 或幻灯片格式）
- ✅ 项目摘要（包括功能概述、用例和核心亮点）
### 🚨 重要：摘要填写规范 (评审关键)
在提交 Pull Request 时，**必须**在描述框中备注以下信息，否则评委可能无法正确归类你的项目：

``
```text
------ 提交信息模板 ------
1. 项目名称: [你的项目名]
2. 参赛赛道: [例如: LLM 应用赛道 (SpoonOS)]
3. 技术栈清单: [例如: SpoonOS, Python, OpenAI API, Kite SDK]
4. 项目简介: [一句话介绍你的项目做什么]
5. Demo 链接/视频: [如果有，请提供]

```
- ✅ 可选：演示视频或用户指南
- ✅ 每个核心团队成员的联系信息（微信 / 邮箱 / 钱包地址）


## 04 | Demo Day 展示指南

**时间：** [DEMO_DAY_DATE_TIME] (UTC+8)

**展示安排：**

- 每个团队一般有 5 - 8 分钟的展示时间，但会视最终提交 Demo 数调整每个项目的具体展示时间——请合理安排时间
- 演示建议内容：
  - 项目介绍
  - 解决的问题
  - 核心功能演示
  - 技术见解
- 项目将按照提交顺序进行展示
- Zoom 链接：[ZOOM_LINK]

## 🏆 奖励与规则(Awards & Evaluation)

### 👥 组队规则
* **自由组队**: 支持跨背景自由组队。
* **人数限制**: 每支参赛队伍成员人数**少于 5 人**。

### 💰 奖励形式
* **总奖金池**: **$2,500 USDT**。
* **奖项设置**: 根据最终报名与参赛人数制定，预计设立**最多 17 个奖项**（覆盖 3 个赛道）。
* **阳光普照奖**: 凡是提交了有效 Demo 的小伙伴，人人可获得**专属社区 Badge**。

### 🎓 身份专属权益
我们对不同背景的选手提供针对性的激励：
* **针对实习计划正式学员**:
    * 瓜分奖金池 + 社区专属 Badge。
    * **额外加成**: 增加**奖励学分**（例如：第一名 +100 学分，后续获奖者 +50 学分）。
* **针对 Permission 学员及外部选手**:
    * 瓜分奖金池 + 社区专属 Badge。
    * *注：Permission 学员不包含学分奖励，重点聚焦于奖金与荣誉勋章。*
*。

### 🔍 评审维度(Judging Criteria)
我们的评审将综合考虑以下四个核心方面：

1.  **技术实现完整度 (Technical Completeness)**
    * 代码是否完整？核心功能是否已通过代码落地？
2.  **Agent / AI 应用合理性 (Agent / AI Rationality)**
    * 是否真正发挥了 AI Agent 的自主性？逻辑是否通顺？
3.  **Web3 场景契合度 (Web3 Fit)**
    * 项目是否解决了 Web3 领域的实际问题（如支付、预测、治理）？
4.  **Demo 可运行性与表达清晰度 (Demo Runnability & Clarity)**
    * Demo 能否顺利演示？README 和文档是否清晰易读？

> ⚠️ **注意**：具体奖金分配细则与奖项设置，将在**黑客松后期统一公布**。

## 05 | 评委阵容

| 姓名           | 身份            | 专长                |
| -------------- | --------------- | ------------------- |
| [JUDGE_1_NAME] | [JUDGE_1_TITLE] | [JUDGE_1_EXPERTISE] |
| [JUDGE_2_NAME] | [JUDGE_2_TITLE] | [JUDGE_2_EXPERTISE] |
| [JUDGE_3_NAME] | [JUDGE_3_TITLE] | [JUDGE_3_EXPERTISE] |
| [JUDGE_4_NAME] | [JUDGE_4_TITLE] | [JUDGE_4_EXPERTISE] |
| [JUDGE_5_NAME] | [JUDGE_5_TITLE] | [JUDGE_5_EXPERTISE] |

## 06 | 奖项设置

| 奖项            | 奖励              | 数量                 |
| --------------- | ----------------- | -------------------- |
| 🥇 一等奖       | [FIRST_PRIZE]     | [FIRST_PRIZE_COUNT]  |
| 🥈 二等奖       | [SECOND_PRIZE]    | [SECOND_PRIZE_COUNT] |
| 🥉 三等奖       | [THIRD_PRIZE]     | [THIRD_PRIZE_COUNT]  |
| 🎖️ 最佳创意奖 | [BEST_IDEA_PRIZE] | [BEST_IDEA_COUNT]    |
| 🎖️ 最佳技术奖 | [BEST_TECH_PRIZE] | [BEST_TECH_COUNT]    |

## 07 | 赞助商与合作伙伴

<table>
    <tr>
        <td align="center" valign="middle">
            <a href="https://x.com/ChainforGood" target="_blank">
                <img src="./materials/images/ChainforGood.png" alt="ChainforGood" width="130" />
            </a>
        </td>
        <td align="center" valign="middle">
            <a href="https://lxdao.io/" target="_blank">
                <img src="./materials/images/LXDAO.png" alt="LXDAO" width="130" />
            </a>
        </td>
        <td align="center" valign="middle">
            <a href="https://ethpanda.org/" target="_blank">
                <img src="./materials/images/ETHPanda.png" alt="ETHPanda" width="130" />
            </a>
        </td>
    </tr>
</table>

### 🌐 社区支持

<table>
    <tr>
        <td align="center" valign="middle">
            <a href="https://x.com/nantangdao/" target="_blank">
                <img src="./materials/images/nantangdao.png" alt="nantangdao" width="130" />
            </a>
        </td>
        <td align="center" valign="middle">
            <a href="https://www.blockchainlabs.org/" target="_blank">
                <img src="./materials/images/blockchainlabs.png" alt="blockchainlabs" width="130" />
            </a>
        </td>
        <td align="center" valign="middle">
            <a href="https://x.com/SmartDeerGlobal" target="_blank">
                <img src="./materials/images/SmartDeer.png" alt="SmartDeer" width="130" />
            </a>
        </td>
        <td align="center" valign="middle">
            <a href="https://x.com/foresight_news?s=21" target="_blank">
                <img src="./materials/images/foresight_news.png" alt="foresight_news" width="130" />
            </a>
        </td>
    </tr>
</table>

## 08 | 报名列表

<!-- Registration start -->
| 姓名 | GitHub ID | 联系方式 | 组队意愿 | 备注 | 更新资料 |
| ---- | ----------- | ----------- | ----------- | ------- | ------- |
| Serena | Serenayyy123 | 微信：shoujiyangt2559 | 愿意！ |感兴趣AI，欢迎大家联系我组队 | [更新](https://github.com/CasualHackathon/agenthack/issues/new?title=Registration%20-%20Serena&body=Name%20%5B%E5%A7%93%E5%90%8D%5D%3A%20Serena%0AContactMethod%20%5B%E8%81%94%E7%B3%BB%E6%96%B9%E5%BC%8F%5D%3A%20%E5%BE%AE%E4%BF%A1%EF%BC%9Ashoujiyangt2559%0AWantsTeam%20%5B%E7%BB%84%E9%98%9F%E6%84%8F%E6%84%BF%5D%3A%20%E6%84%BF%E6%84%8F%EF%BC%81%0AComment%20%5B%E5%A4%87%E6%B3%A8%5D%3A%20%E6%84%9F%E5%85%B4%E8%B6%A3AI%EF%BC%8C%E6%AC%A2%E8%BF%8E%E5%A4%A7%E5%AE%B6%E8%81%94%E7%B3%BB%E6%88%91%E7%BB%84%E9%98%9F) |
| 测试 | beetroot42 | 测试 | 测试 |测试 | [更新](https://github.com/CasualHackathon/agenthack/issues/new?title=Registration%20-%20%E6%B5%8B%E8%AF%95&body=Name%20%5B%E5%A7%93%E5%90%8D%5D%3A%20%E6%B5%8B%E8%AF%95%0AContactMethod%20%5B%E8%81%94%E7%B3%BB%E6%96%B9%E5%BC%8F%5D%3A%20%E6%B5%8B%E8%AF%95%0AWantsTeam%20%5B%E7%BB%84%E9%98%9F%E6%84%8F%E6%84%BF%5D%3A%20%E6%B5%8B%E8%AF%95%0AComment%20%5B%E5%A4%87%E6%B3%A8%5D%3A%20%E6%B5%8B%E8%AF%95) |
| 测试 | lejusuelge-star | 测试 | 测啊 |测试 | [更新](https://github.com/CasualHackathon/agenthack/issues/new?title=Registration%20-%20%E6%B5%8B%E8%AF%95&body=Name%20%5B%E5%A7%93%E5%90%8D%5D%3A%20%E6%B5%8B%E8%AF%95%0AContactMethod%20%5B%E8%81%94%E7%B3%BB%E6%96%B9%E5%BC%8F%5D%3A%20%E6%B5%8B%E8%AF%95%0AWantsTeam%20%5B%E7%BB%84%E9%98%9F%E6%84%8F%E6%84%BF%5D%3A%20%E6%B5%8B%E5%95%8A%0AComment%20%5B%E5%A4%87%E6%B3%A8%5D%3A%20%E6%B5%8B%E8%AF%95) |

<!-- Registration end -->

## 09 | 提交名单

<!-- Submission start -->
| 项目名称 | GitHub ID | 项目描述 | 项目链接 | 提交时间 |
| ----------- | ----------------- | -------------- | ------ | -------- |
| Spark AI | Serenayyy123 | test | [Repo](https://github.com/Serenayyy123/EverEcho-on-ZetaChain) \| [Folder](https://github.com/CasualHackathon/agenthack/tree/main/submissions/Serenayyy123) | - |
| 测试 | beetroot42 | 测试 | [Repo](测试) \| [Folder](https://github.com/CasualHackathon/agenthack/tree/main/submissions/beetroot42) | - |

<!-- Submission end -->

## 🔗 快速链接

- 📝 [报名表单][REGISTRATION_FORM_LINK]
- 🎥 [教程视频 - Bilibili][VIDEO_TUTORIAL_BILIBILI]
- 🎥 [教程视频 - YouTube][VIDEO_TUTORIAL_YOUTUBE]
- 💬 [社区讨论](https://github.com/CasualHackathon/agenthack/discussions)
- 🐛 [问题反馈](https://github.com/CasualHackathon/agenthack/issues)

## ℹ️ 常见问题 (FAQ)

**Q: 我没有技术背景可以参加吗？**
A: 完全可以！我们鼓励非技术背景的参赛者参加。你可以专注于产品设计、运营策划、市场营销等方面，或者使用 AI 工具辅助。

**Q: 团队人数有限制吗？**
A: 没有硬性限制，建议 1-5 人组队效率最高。

**Q: 必须是 Web3 相关项目吗？**
A: 项目需要与 [ACTIVITY_THEME] 相关即可。

**Q: 代码必须在黑客松期间完成吗？**
A: 是的，所有代码需要在活动期间提交。可以基于现有框架进行开发。

**Q: 获奖后有什么后续支持？**
A: [FOLLOW_UP_SUPPORT]

## 📧 联系我们

- **主办方：** 残酷共学
- **技术支持：** [TECH_CONTACT_EMAIL]
- **运营协调：** [OPS_CONTACT_EMAIL]
- **微信社群：** [WECHAT_GROUP_INFO]

## 📜 许可证

[LICENSE_TYPE]

<img width="2560" height="1440" alt="image" src="https://github.com/user-attachments/assets/382c6d08-1bad-421b-97aa-3a4e17542f4c" />

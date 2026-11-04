# Tender × DAOQL 白皮书协作说明

## 在线阅读

- 在线源文档：<https://github.com/MK60DN/Tender/blob/main/docs/whitepaper/Tender-DAOQL-Data-Water-Whitepaper-v1.0.md>
- Markdown 源文档：[Tender-DAOQL-Data-Water-Whitepaper-v1.0.md](whitepaper/Tender-DAOQL-Data-Water-Whitepaper-v1.0.md)
- PDF：[Tender-DAOQL-Data-Water-Whitepaper-v1.0.pdf](whitepaper/Tender-DAOQL-Data-Water-Whitepaper-v1.0.pdf)

## 编辑方式

### 方式一：有仓库写权限，直接编辑

适合合伙人、研究负责人、法务/品牌审核人和被邀请的编辑。

1. 打开博客页顶部的“在 GitHub 编辑”。
2. 登录 GitHub。
3. 修改 Markdown。
4. 提交到新分支并创建 Pull Request；拥有直接写权限时也可按团队规范直接提交。
5. 由维护者合并后，同步更新博客发布快照。

### 方式二：没有仓库权限，提交 PR

1. 打开 Markdown 源文档。
2. 点击 GitHub 页面右上角的 Fork。
3. 在自己的 Fork 中编辑。
4. 向上游仓库 MK60DN/Tender 提交 Pull Request。
5. 在 PR 中说明修改了哪一节、为什么修改、依据是什么。

### 方式三：只提意见，不直接改

使用博客页顶部的“提交修改建议”，或在 GitHub 新建 Issue：

- 事实纠错；
- 论证补充；
- 文献/数据来源；
- 合规与风险提示；
- 结构与措辞建议；
- 需要新增的章节。

## 邀请外部编辑

由仓库所有者或管理员操作：

1. 打开 GitHub 仓库 Settings。
2. 进入 Collaborators and teams。
3. 点击 Add people，输入对方 GitHub 用户名。
4. 建议授予 Write，不要默认授予 Admin。
5. 如仓库属于组织，可建立 whitepaper-editors Team，授予 Write 权限。

若对方不希望成为仓库协作者，使用 Fork + Pull Request 即可，不需要授予仓库权限。

## 编辑规则

1. **保持状态标签。** 区分“已实现”“已有基础”“目标架构”“研究假设”，不要把愿景写成已交付。
2. **不加入未经核实的数字。** 新数据必须注明测试条件、样本、来源和边界。
3. **不承诺投资收益。** 贡献积分、Token、收益分配必须经过法律与合规审查，禁止写成固定收益或升值承诺。
4. **不泄露个人隐私。** 受益人、学生、患者、家庭和合作机构的可识别信息不得写入公开文档。
5. **保留反方观点。** 高风险章节应同时保留风险、失败模式与退出机制。
6. **版本与日期。** 修改实质性内容时更新 front matter 的 version/date，并在 PR 中说明。
7. **引用可追溯。** 新增事实优先使用机构官网、论文、标准、正式报告或一手文件。

## 建议审阅角色

- 产品/架构：确认 DaoQL 与 Tender 的现状边界；
- 研究：确认实验、指标和因果关系表述；
- 法务/合规：确认 Token、收益分配、数据与慈善监管表述；
- 品牌/传播：确认标题、摘要和对外口径；
- 安全/隐私：确认未成年人、临床、高敏感受益人数据边界。

## 发布流程

1. 修改 Markdown 并提交 PR。
2. 至少一位维护者审核。
3. 合并到 main。
4. 如修改影响对外博客，维护者同步更新 site/whitepaper.html 并推送。
5. GitHub Pages 自动部署 site/ 更新。

## PR 最低验收清单

- [ ] 没有把目标架构写成当前能力
- [ ] 没有未经核实的数字或来源
- [ ] 没有固定收益、升值或代币发行承诺
- [ ] 没有个人或受益人隐私
- [ ] 已更新版本号/日期
- [ ] 已说明修改依据
- [ ] 如更新了博客页，已完成链接检查

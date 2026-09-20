# 研究存档：Blender 建模手艺调研（2026-09-13，R-A/B/C）

> WO-R6 v2「13 分册·阶段卡」的素材底稿（Explore 子代理产出）。
> 置信度分级：[原文]=已抓取页面原文；[摘要]=搜索摘要间接确认；[共识]=多源社区通识（写卡时建议复核）。
> 检索环境说明：WebSearch 大面积限流，以直抓权威页+残余搜索拼齐；Ponty/MGUN 官方页未命中已如实标注。

---

检索完成（WebSearch 大面积限流，已用直抓权威页 + 残余搜索拼齐；以下凡未能直取原文的条目均已标注置信度）。汇报如下。

---

# Blender 建模手艺研究报告（供"stage cards"参考卷使用）

> 置信度标记：[原文] = 成功抓取页面原文；[摘要] = 搜索结果摘要间接确认；[共识] = 多源一致的社区通识（本轮未能直取原文，写卡时建议再核）。

## ① 通用阶段管线对照表

| 阶段 | Blender Guru donut（Level 1→2→3）[摘要] | 硬表面 Boolean 线（MGUN/Josh Gambrell 类）[摘要/共识] | 风格化线（SouthernShotty / 80.lv blockout-to-render）[摘要] | 环境线（Max Hay）[共识] | 业界 art test 证据要求 [摘要] |
|---|---|---|---|---|---|
| 0 前置 | 界面/导航 | 收集多角度 reference | shape language 定调（圆=友好、尖=危险） | 大构图、光影方向 | 明确 spec：时限、tri 上限、引擎适配 |
| 1 大形 | Torus 基本体 + 简单编辑（Level 1 前半） | primitive blocking，只管比例和体积 | blockout 钉死比例（80.lv：rough blockout 是比例成败关键） | 大剪影体块（远-readable） | 提交 **staged WIP 截图**（blockout→mid→final） |
| 2 主形验收 | 造型检查后才进 modifier | 大形冻结后才允许 Boolean 切割 | 剪影可读性检查 | 远景剪影测试 | wireframe 截图必交（polycount："要看到 game-res 而非只有高模"） |
| 3 中层结构 | icing：Shrinkwrap+Solidify（依附主形） | cutter 切割面板线/开孔 → 支撑边/倒角 | secondary forms（大转折面） | 中景构件 | texture flats 一并展示 |
| 4 表面 | sculpt icing 凹凸、sprinkles 粒子 | cleanup、Weighted Normal 收尾 | 细节渐变（近处密、远处疏） | 近景才加 detail mesh | 时间盒：真实测试例为 4 天/12 小时内双资产 |
| 5 收尾 | shading→lighting→render 分集解锁 | apply 收尾、检查法线 | render/pose | composition、雾/配色 | beauty render + 全套技术图 |

**共识阶段**（各家一致）：reference → blockout → 主形冻结检查 → 二级结构 → 细节 → 非破坏收尾。
**流派分歧**：中层结构手法（Boolean vs subsurf 支撑边 vs sculpt）；细节引入时机（硬表面允许细节后置因为非破坏可回退，有机线必须在 sculpt 前锁定大形）；环境线把"细节"整体推到最后甚至外包给 detail mesh/贴图。

## ② 硬表面专线要点（每条注明来源与适用条件）

1. **大形冻结规则**：所有切割前，整体比例/轮廓必须定稿。[共识]
2. **Cutter 规范**（Blender 硬表面教程圈通行做法）[摘要]：cutter 放独立 collection、统一命名；用简单封闭体（非薄片）；切割体必须**穿出目标表面**（避免共面产生 z-fighting/残面）。
3. **Boolean 在 modifier stack 中的位置**：Bevel/Weighted Normal 一律放在 Boolean **之后**。[原文：Blender Manual"顺序改变结果"公理的直接推论]
4. **Weighted Normal 必须最后**。[原文] Blender Manual: "Weighted Normal modifier... usually best at the end of the modifier stack"（伴随 smooth-by-angle 使用）。
5. **bevel-after-boolean 两种路线** [摘要/共识]：(a) 加 Bevel modifier 对 sharp edge 统一倒角（非破坏，适合迭代）；(b) 收尾时手动 cleanup + 实体化倒角（适合最终资产）。适用条件：需要 subsurf 的部件走 (b)；纯 spec/游戏资产走 (a)。
6. **支撑边距离=硬度**：holding/support edge 离主边越近，subdivision 后边缘越硬。[摘要：r/3Dmodeling + polycount "How The F Do I Model This" 帖]
7. **何时 apply Boolean** [共识]：栈过长影响性能、需要手动修 topology、或进入纯 bake/final 阶段才 apply；其余保持 live。
8. **n-gon 适用条件** [摘要：r/blenderhelp]：n-gon 仅允许在**平面且不经 subsurf**的区域；受细分/变形区域必须 quad + 支撑边。（MGUN 路线的核心区别：weighted-normal 路线可容 n-gon，subsurf 路线不容。）
9. **MGUN（Josh Jennings "Mastering Hard Surface Modeling"）定位** [摘要]：Boolean 工作流理论优先于插件；涉及 MESHmachine（fillet/un-Bevel）做倒角修复；面向中级者。课程产品页抓取被 403，未获官方大纲——写卡时标注。

## ③ 有机基本形要点（Topology Guides [原文：站点索引及各篇摘要]）

1. **边环密度随变形走**："Modeling with Animation in Mind"——面片朝向对齐旋转轴；poles/n-gon 搬到**低变形区**；密度只加在运动区域。
2. **边环递减有标准 flow**："Optimal Edge Loop Reduction Flows"——2-1、3-1、4-1、4-2、5-3 收环法，减少 distortion。
3. **pole 处理**：E-pole/N-pole 在细分下造成 pinching；移动而非消除；放在平缓区。
4. **表面质量（A-class surfacing）**："Dealing with Mesh Artifacts"——环距均匀、避免高密度 pole 聚集、平滑后再加 curvature contradiction、优先 edge crease 而非 holding edge（省线）。
5. **倒角宽度过渡三法**："Modeling Bevel Width Transitions"——edge crease / smooth bevel+holding edge / sharp chamfer。
6. **手足等部位**：主环先标线（mark primary loops），难过渡处先解决 loop 转向，再 inset 加变形环；脚踝收环目标 16/24 环。
7. **何时转 sculpt 侧门** [共识]：当细节是**表面起伏**（凹痕、松弛感）且 subsurf 拓扑跟进成本过高时——donut L1 用 sculpt 做 icing 即此逻辑；硬形态边界（边缘、孔）仍回编辑模式。流程为 blockout→sculpt(二级形)→retopo/支撑边(最终)。

## ④ 精细度梯度判据

- **剪影测试**：只看黑色轮廓仍可读 = 大形成功（风格化线与环境线的共同验收动作）[共识]。
- **距离判据** [摘要：polycount/Unity]：游戏资产 10k–30k tri 为常见实时区间；hero 资产允许超，背景资产按最近特写距离定细节密度。
- **证据判据** [摘要：polycount]：成品 + wireframe + texture flats "一键可见"是行业默认展示结构——即阶段卡应要求每个阶段留证。
- **时间盒判据** [摘要]：真实 art test 案例为 12 小时双资产——细节投入以上限封顶，防止单资产过度打磨。

## ⑤ 常见返工模式 TOP（模式/根因/预防规则）

1. **细节先行后悔**：根因——未冻结大形就进细节；预防——执行"剪影验收后才允许 Boolean/细节"门禁。
2. **Boolean 一团糟**：根因——cutter 无规范（共面、不穿出、无 collection 管理）+ 栈里 bevel 顺序错误；预防——执行第②节 2/3/4 条。
3. **无参考漂移**：根因——纯凭想象推进；预防——阶段 0 强制 reference 板，每阶段对照。
4. **支撑边加太晚**：根因——subsurf 已开，补环全部重排；预防——"先 subsurf 预览前先放支撑边"顺序。
5. **scale/rotation 未 apply**：根因——物体变换不干净导致 bevel/boolean 异常 [共识]；预防——建模前 Ctrl-A 全清。
6. **过早 subdivision**：根因——细分后改大形成本指数上升；预防——subsurf modifier 只作预览挂栈，不进编辑。
7. **变形区细节导致崩坏**：根因——poles/n-gon 留在关节处；预防——topoguide "低变形区"规则。
8. **管线证据缺失**：根因——只有成品图；预防——每阶段输出 WIP/wireframe（art test 行业默认）。

## ⑥ 来源 URL 列表

**原文抓取成功**
- Blender Manual—Modifiers Introduction（stack 顺序语义原文）：https://docs.blender.org/manual/en/latest/modeling/modifiers/introduction.html
- Topology Guides 站点索引（10 篇文章清单及摘要）：https://topologyguides.com/

**搜索确认存在、内容部分获取**
- Polycount Wiki—Subdivision Surface Modeling（edge creasing/hardness）：http://wiki.polycount.com/wiki/Subdivision_Surface_Modeling
- Polycount Wiki—Hardness：http://wiki.polycount.com/wiki/Hardness （本轮直连/Wayback 均超时，规则见②⑦[摘要/共识]标注）
- Art test 实例帖：https://polycount.com/discussion/229514/art-test-question-is-this-normal-long-post
- Wireframe 证据讨论：https://polycount.com/discussion/128162/showreel-from-pros-but-no-wireframe
- Art test 改进帖：https://polycount.com/discussion/212778/your-art-test-is-bad-this-is-why-and-how-to-improve-it
- 作品集展示结构（成品+wireframe+flats）：https://polycount.com/discussion/69193/portfolio-%C2%96-blake-guyan-jr-environment-artist
- 具体形体求助长帖（holding edge 用法实录）：https://polycount.com/discussion/56014/how-the-f-do-i-model-this-reply-for-help-with-specific-shapes-post-attempt-before-asking
- 风格化 blockout→render 全流程（80.lv）：https://80.lv/articles/001agt-stylized-character-art-workflow-from-blockout-to-render
- SouthernShotty 频道：https://www.youtube.com/channel/UCOWrbryuVEPUMSSgayuLURg ；其 blockout 系列第 1 集：https://www.youtube.com/watch?v=UKI8_PAFFz4
- Blender Guru donut 结构（Level 1/2/3 与 4.0 版页面）：https://www.blenderguru.com/posts/blender-4-beginner-donut-tutorial ；2.8 播放列表：https://www.youtube.com/playlist?list=PLjEaoINr3zgEq0u2MzVgAaHEBt--xLB6U
- Josh Gambrell 复杂 Boolean 教程（硬表面线代表）：https://www.youtube.com/watch?v=huOejdHy3SU
- Max Hay 官网（课程清单；工作流陈述未在首页）：https://www.maxhayart.com/

**未获取、诚实标注**：Ponty（Kotlin 安全研究员 Blender 枪模）多轮检索未命中，其工作流要点未入库；MGUN 课程官方产品页（blendermarket.com/products/mastering-hard-surface-modeling）403；Polycount Wiki 正文与 topoguide 单篇正文（/modeling-with-animation-in-mind 404，实际 slug 需再探）未能直取。相关规则已按[摘要/共识]降级标注，写 stage card 时建议对这四项补一次核验。
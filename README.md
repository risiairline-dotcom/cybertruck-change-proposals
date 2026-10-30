# 初赛整机实施提案

目标：2026年11月6日湖南省赛，先稳定完成初赛，再优化速度和精度；决赛后置。

- [详细实施方案与持续迭代约定](docs/preliminary_execution_plan_20261030.md)
- [Claude Code执行入口](CLAUDE.md)
- [视觉与整机开发方案 v2](docs/vision_development_plan_20261030.md)
- [两轮视觉方案评审与裁决](docs/vision_review_20261030.md)
- [圆心算法离线复现结果](evidence/ring_refiner_review_20261030.json)
- [63项整机审计与可行性分析](docs/provincial_system_audit_20261030.md)
- [电脑B视觉工作范围参考](docs/vision_B_plan_20261030.md)
- [四项离线问题复现结果](evidence/offline_reproductions.json)

实施排期以详细方案为准，B任务单中的日期是历史目标。方案不表示功能已完成：+Y实物未通过，完整初赛尚未验收。源码引用基线为cybertruck的6f8694f。规则PDF未上传，应另核对原件及现场补充。

视觉最新实施细节以v2方案为准，与整机方案共同使用。Claude Code从CLAUDE.md开始；V0/V1离线工作先行，按数据选择圆心、颜色或二维码候选，尽早验证单件循环。控制代码修改与设备操作的既有暂停没有因上传方案而解除。

圆心复现仅需兼容的NumPy与OpenCV，建议独立环境，不更改当前Pi依赖：

```text
python tools/reproduce_ring_review.py --output ring_review.local.json
```

本次证据环境为OpenCV 5.0.0、NumPy 2.5.4；目标Pi兼容与性能另验。tools/reviewed_ring_candidates.py保留有缺陷的被评审函数，仅用于对照，不是生产实现。生成的本地报告不要覆盖已发布证据后宣称为原实验。

158项回归及四项复现属于此前审计结果；本次上传未操作设备、部署或烧录。
